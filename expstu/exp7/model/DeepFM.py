import os
import torch
import torch.nn as nn
import torch.nn.functional as F


class DeepFM(nn.Module):
    def __init__(self, feature_sizes, embedding_size=4,
                 hidden_dims=None, num_classes=1, dropout=None,
                 use_cuda=True, verbose=False):
        if hidden_dims is None:
            hidden_dims = [32, 32]
        if dropout is None:
            dropout = [0.5, 0.5]

        super(DeepFM, self).__init__()
        self.field_size = len(feature_sizes)
        self.feature_sizes = feature_sizes
        self.embedding_size = embedding_size
        self.hidden_dims = hidden_dims
        self.num_classes = num_classes
        self.verbose = verbose

        # FM first-order embeddings (dim=1 per field, like LR weights)
        self.fm_first_order_embeddings = nn.ModuleList(
            [nn.Embedding(feature_size, 1) for feature_size in self.feature_sizes])

        # FM second-order embeddings (dim=embedding_size, shared with DNN)
        self.fm_second_order_embeddings = nn.ModuleList(
            [nn.Embedding(feature_size, self.embedding_size) for feature_size in self.feature_sizes])

        # DNN hidden layers
        all_dims = [self.field_size * self.embedding_size] + self.hidden_dims + [self.num_classes]
        for i in range(1, len(hidden_dims) + 1):
            setattr(self, 'linear_' + str(i), nn.Linear(all_dims[i - 1], all_dims[i]))
            setattr(self, 'batchNorm_' + str(i), nn.BatchNorm1d(all_dims[i]))
            setattr(self, 'dropout_' + str(i), nn.Dropout(dropout[i - 1]))

        # Global bias
        self.bias = nn.Parameter(torch.randn(1))

        if use_cuda and torch.cuda.is_available():
            self.device = torch.device('cuda')
        else:
            self.device = torch.device('cpu')

        self.to(self.device)
        if verbose:
            total_params = sum(p.numel() for p in self.parameters())
            print(f'DeepFM: {total_params:,} params, field_size={self.field_size}, '
                  f'embedding_size={self.embedding_size}, hidden_dims={self.hidden_dims}')

    def forward(self, Xi, Xv):
        # Xi: (batch_size, field_size, 1)
        # Xv: (batch_size, field_size)

        # FM first-order: linear weights for each field
        fm_first_order_emb_arr = [
            (torch.sum(emb(Xi[:, i, :]), 1).t() * Xv[:, i]).t()
            for i, emb in enumerate(self.fm_first_order_embeddings)
        ]
        fm_first_order = torch.cat(fm_first_order_emb_arr, 1)  # (batch, field_size)

        # FM second-order embeddings (shared with DNN)
        fm_second_order_emb_arr = [
            (torch.sum(emb(Xi[:, i, :]), 1).t() * Xv[:, i]).t()
            for i, emb in enumerate(self.fm_second_order_embeddings)
        ]

        # FM second-order interaction: 0.5 * [(sum v_i*x_i)^2 - sum (v_i*x_i)^2]
        fm_sum_second_order_emb = sum(fm_second_order_emb_arr)
        fm_sum_second_order_emb_square = fm_sum_second_order_emb * fm_sum_second_order_emb

        fm_second_order_emb_square = [item * item for item in fm_second_order_emb_arr]
        fm_second_order_emb_square_sum = sum(fm_second_order_emb_square)

        fm_second_order = (fm_sum_second_order_emb_square - fm_second_order_emb_square_sum) * 0.5

        # DNN: feed shared embeddings through deep layers
        deep_emb = torch.cat(fm_second_order_emb_arr, 1)  # (batch, field_size * emb_size)
        deep_out = deep_emb

        for i in range(1, len(self.hidden_dims) + 1):
            deep_out = getattr(self, 'linear_' + str(i))(deep_out)
            deep_out = getattr(self, 'batchNorm_' + str(i))(deep_out)
            deep_out = getattr(self, 'dropout_' + str(i))(deep_out)

        # Combined output: sum contributions from all three components + bias
        total_sum = (
            torch.sum(fm_first_order, 1)
            + torch.sum(fm_second_order, 1)
            + torch.sum(deep_out, 1)
            + self.bias
        )

        return total_sum

    def fit(self, loader_train, loader_val, epochs=10, lr=1e-3,
            weight_decay=0.0, print_every=100, early_stop_patience=None):
        model = self.train().to(device=self.device)
        criterion = F.binary_cross_entropy_with_logits
        optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)

        best_val_acc = 0.0
        patience_counter = 0

        for epoch in range(epochs):
            model.train()
            total_loss = 0.0
            num_batches = 0

            for t, (xi, xv, y) in enumerate(loader_train):
                xi = xi.to(device=self.device, dtype=torch.long)
                xv = xv.to(device=self.device, dtype=torch.float)
                y = y.to(device=self.device, dtype=torch.float).view(-1)

                total = model(xi, xv)
                loss = criterion(total, y)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                total_loss += loss.item()
                num_batches += 1

                if self.verbose and t > 0 and t % print_every == 0:
                    print(f'Iteration {t}, loss = {loss.item():.4f}')
                    self.check_accuracy(loader_val, model)

            avg_loss = total_loss / max(num_batches, 1)
            val_acc = self.check_accuracy(loader_val, model)

            if self.verbose:
                print(f'Epoch {epoch + 1}: avg_loss = {avg_loss:.4f}, val_acc = {val_acc:.4f}')

            if early_stop_patience is not None:
                if val_acc > best_val_acc:
                    best_val_acc = val_acc
                    patience_counter = 0
                    torch.save(model.state_dict(), 'best_model.pth')
                else:
                    patience_counter += 1
                    if patience_counter >= early_stop_patience:
                        if self.verbose:
                            print(f'Early stopping at epoch {epoch + 1}')
                        break

        if early_stop_patience is not None and os.path.exists('best_model.pth'):
            self.load_state_dict(torch.load('best_model.pth'))

    def check_accuracy(self, loader, model=None):
        if model is None:
            model = self
        was_training = model.training
        model.eval()
        num_correct = 0
        num_samples = 0
        with torch.no_grad():
            for xi, xv, y in loader:
                xi = xi.to(device=self.device, dtype=torch.long)
                xv = xv.to(device=self.device, dtype=torch.float)
                y = y.to(device=self.device, dtype=torch.float).view(-1)

                total = model(xi, xv)
                preds = (torch.sigmoid(total) > 0.5).float()
                num_correct += (preds == y).sum().item()
                num_samples += len(y)

        acc = float(num_correct) / max(num_samples, 1)
        if was_training:
            model.train()
        if self.verbose and model is self:
            print(f'  val_acc = {acc:.4f}')
        return acc
