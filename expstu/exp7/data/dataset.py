import torch
from torch.utils.data import Dataset
import numpy as np
import os
import pickle


class CriteoDataset(Dataset):
    def __init__(self, data_path, train=True, vocab_path=None, cutoff=10):
        self.data_path = data_path
        self.train = train
        self.continuous_fields = 13
        self.categorical_fields = 26
        self.field_size = self.continuous_fields + self.categorical_fields

        if train:
            data_file = os.path.join(data_path, 'train.txt')
        else:
            data_file = os.path.join(data_path, 'test.txt')

        # Read raw data
        self.raw_data = []
        with open(data_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split('\t')
                self.raw_data.append(parts)

        if train:
            self._build_vocab(cutoff)
        else:
            self._load_vocab(vocab_path)

        self.feature_sizes = [1] * self.continuous_fields + self.categorical_sizes

    def _build_vocab(self, cutoff):
        # Count frequencies for each categorical field
        cat_freqs = [{} for _ in range(self.categorical_fields)]
        for parts in self.raw_data:
            for i in range(self.categorical_fields):
                col_idx = self.continuous_fields + 1 + i  # +1 for label
                val = parts[col_idx] if col_idx < len(parts) else ''
                if val and val.strip():
                    val = val.strip()
                    cat_freqs[i][val] = cat_freqs[i].get(val, 0) + 1

        # Build vocabulary: filter by cutoff, sort by frequency
        self.categorical_vocabs = []
        self.categorical_sizes = []
        for freq_dict in cat_freqs:
            # Filter by cutoff, sort by frequency descending
            valid = [(v, k) for k, v in freq_dict.items() if v >= cutoff]
            valid.sort(reverse=True)
            # Index 0 reserved for <unk>
            vocab = {k: idx + 1 for idx, (_, k) in enumerate(valid)}
            self.categorical_vocabs.append(vocab)
            self.categorical_sizes.append(len(vocab) + 1)  # +1 for <unk>

        # Save vocabs
        vocab_path = os.path.join(self.data_path, 'categorical_vocabs.pkl')
        with open(vocab_path, 'wb') as f:
            pickle.dump(self.categorical_vocabs, f)

        # Save feature sizes
        sizes_path = os.path.join(self.data_path, 'feature_sizes.txt')
        with open(sizes_path, 'w') as f:
            sizes = [1] * self.continuous_fields + self.categorical_sizes
            for s in sizes:
                f.write(f'{s}\n')

    def _load_vocab(self, vocab_path):
        if vocab_path is None:
            vocab_path = os.path.join(self.data_path, 'categorical_vocabs.pkl')
        with open(vocab_path, 'rb') as f:
            self.categorical_vocabs = pickle.load(f)
        self.categorical_sizes = [len(v) + 1 for v in self.categorical_vocabs]

    def __len__(self):
        return len(self.raw_data)

    def __getitem__(self, idx):
        parts = self.raw_data[idx]

        # Label (first field)
        label = float(parts[0]) if parts[0] else 0.0

        # Xi: feature indices, shape (field_size, 1)
        # Xv: feature values, shape (field_size,)
        Xi = np.zeros((self.field_size, 1), dtype=np.int64)
        Xv = np.zeros(self.field_size, dtype=np.float32)

        # Continuous features (fields 1-13)
        for i in range(self.continuous_fields):
            col_idx = i + 1  # +1 for label
            val_str = parts[col_idx] if col_idx < len(parts) else ''
            if not val_str or not val_str.strip():
                val = 0.0
            else:
                val = float(val_str)
            Xi[i, 0] = 0  # continuous features always index 0
            Xv[i] = np.log1p(max(val, 0.0))

        # Categorical features (fields 14-39)
        for i in range(self.categorical_fields):
            col_idx = self.continuous_fields + 1 + i  # +1 for label
            val = parts[col_idx] if col_idx < len(parts) else ''
            val = val.strip() if val else ''
            vocab = self.categorical_vocabs[i]
            Xi[self.continuous_fields + i, 0] = vocab.get(val, 0)  # 0 for <unk>
            Xv[self.continuous_fields + i] = 1.0

        return (
            torch.LongTensor(Xi),
            torch.FloatTensor(Xv),
            torch.FloatTensor([label]),
        )
