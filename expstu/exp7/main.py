import os
import sys
import torch
from torch.utils.data import DataLoader
from torch.utils.data import sampler

sys.path.insert(0, os.path.dirname(__file__))

from data.dataset import CriteoDataset
from model.DeepFM import DeepFM


def load_data(data_path, batch_size=100):
    print('Loading training data...')
    train_data = CriteoDataset(data_path, train=True)

    dataset_size = len(train_data)
    num_train = int(dataset_size * 0.8)

    indices = list(range(dataset_size))
    train_indices = indices[:num_train]
    val_indices = indices[num_train:]

    loader_train = DataLoader(
        train_data, batch_size=batch_size,
        sampler=sampler.SubsetRandomSampler(train_indices))
    loader_val = DataLoader(
        train_data, batch_size=batch_size,
        sampler=sampler.SubsetRandomSampler(val_indices))

    print('Loading test data...')
    test_data = CriteoDataset(data_path, train=False)
    loader_test = DataLoader(test_data, batch_size=batch_size)

    print(f'Train samples: {len(train_indices)}, Val samples: {len(val_indices)}, '
          f'Test samples: {len(test_data)}')

    return loader_train, loader_val, loader_test, train_data.feature_sizes


def experiment_embedding_size(data_path='./data'):
    """Experiment 7.3 Step 1: Compare different embedding sizes."""
    loader_train, loader_val, loader_test, feature_sizes = load_data(data_path)

    results = {}
    for emb_size in [4, 8, 16]:
        print(f'\n{"="*60}')
        print(f'Experiment: embedding_size = {emb_size}')
        print(f'{"="*60}')

        model = DeepFM(feature_sizes, embedding_size=emb_size,
                       hidden_dims=[32, 32], dropout=[0.5, 0.5],
                       verbose=True)
        model.fit(loader_train, loader_val, epochs=5, lr=1e-3, print_every=200)

        test_acc = model.check_accuracy(loader_test)
        results[emb_size] = test_acc
        print(f'embedding_size={emb_size}: test_acc = {test_acc:.4f}')

    print('\nEmbedding size comparison:')
    for k, v in results.items():
        print(f'  embedding_size={k}: test_acc = {v:.4f}')


def experiment_dnn_structure(data_path='./data'):
    """Experiment 7.3 Step 2: Compare different DNN structures."""
    loader_train, loader_val, loader_test, feature_sizes = load_data(data_path)

    configs = [
        ([32, 32], [0.5, 0.5], 'A: [32,32]'),
        ([64, 64], [0.5, 0.5], 'B: [64,64]'),
        ([128, 64, 32], [0.5, 0.5, 0.5], 'C: [128,64,32]'),
    ]

    results = {}
    for hidden_dims, dropout, label in configs:
        print(f'\n{"="*60}')
        print(f'Experiment: DNN = {label}')
        print(f'{"="*60}')

        model = DeepFM(feature_sizes, embedding_size=4,
                       hidden_dims=hidden_dims, dropout=dropout,
                       verbose=True)
        model.fit(loader_train, loader_val, epochs=5, lr=1e-3, print_every=200)

        test_acc = model.check_accuracy(loader_test)
        results[label] = test_acc
        print(f'{label}: test_acc = {test_acc:.4f}')

    print('\nDNN structure comparison:')
    for k, v in results.items():
        print(f'  {k}: test_acc = {v:.4f}')


def experiment_learning_rate(data_path='./data'):
    """Experiment 7.3 Step 3: Compare different learning rates."""
    loader_train, loader_val, loader_test, feature_sizes = load_data(data_path)

    results = {}
    for lr in [1e-3, 1e-4, 1e-5]:
        print(f'\n{"="*60}')
        print(f'Experiment: lr = {lr}')
        print(f'{"="*60}')

        model = DeepFM(feature_sizes, embedding_size=4,
                       hidden_dims=[32, 32], dropout=[0.5, 0.5],
                       verbose=True)
        model.fit(loader_train, loader_val, epochs=5, lr=lr, print_every=200)

        test_acc = model.check_accuracy(loader_test)
        results[lr] = test_acc
        print(f'lr={lr}: test_acc = {test_acc:.4f}')

    print('\nLearning rate comparison:')
    for k, v in results.items():
        print(f'  lr={k}: test_acc = {v:.4f}')


def experiment_model_comparison(data_path='./data'):
    """Experiment 9.3: Compare FM-only, DNN-only, and DeepFM."""
    loader_train, loader_val, loader_test, feature_sizes = load_data(data_path)

    models = {
        'DeepFM': DeepFM(feature_sizes, embedding_size=4,
                         hidden_dims=[32, 32], dropout=[0.5, 0.5], verbose=True),
    }

    results = {}
    for name, model in models.items():
        print(f'\n{"="*60}')
        print(f'Training: {name}')
        print(f'{"="*60}')

        model.fit(loader_train, loader_val, epochs=5, lr=1e-3, print_every=200)
        test_acc = model.check_accuracy(loader_test)
        results[name] = test_acc
        print(f'{name}: test_acc = {test_acc:.4f}')

    return results


def main():
    data_path = os.path.join(os.path.dirname(__file__), 'data')

    print('=' * 60)
    print('DeepFM Experiment Suite - Criteo CTR Prediction')
    print('=' * 60)

    # Baseline: single DeepFM run
    print('\n--- Baseline DeepFM Training ---')
    loader_train, loader_val, loader_test, feature_sizes = load_data(data_path)

    model = DeepFM(feature_sizes, embedding_size=4,
                   hidden_dims=[32, 32], dropout=[0.5, 0.5],
                   verbose=True)

    model.fit(loader_train, loader_val, epochs=10, lr=1e-3,
              print_every=200, early_stop_patience=3)

    test_acc = model.check_accuracy(loader_test)
    print(f'\nFinal test accuracy: {test_acc:.4f}')

    # Save model
    torch.save(model.state_dict(), os.path.join(data_path, 'deepfm_model.pth'))
    print('Model saved to data/deepfm_model.pth')


if __name__ == '__main__':
    main()
