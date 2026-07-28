# MLflow Autologging with PyTorch

**Notebook 2 of 3** · Demo for the "MLflow: Autologging & Zero-Config" talk

Here's the catch most tutorials skip: **`mlflow.autolog()` does not work on a raw PyTorch training loop.** A hand-written loop has no standard hook for MLflow to grab.

The fix is **PyTorch Lightning**, which gives autolog the structure it needs. This notebook shows both:
- Part A: the Lightning way (autolog works).
- Part B: the raw-loop way (manual logging).

Find more at [thamu.dev](https://thamu.dev/).

## Setup


```python
# uv:   !uv pip install "mlflow>=3.1" torch lightning torchvision
# pip:  !pip install "mlflow>=3.1" torch lightning torchvision

import mlflow, torch, lightning as L
print("mlflow    :", mlflow.__version__)
print("torch     :", torch.__version__)
print("lightning :", L.__version__)
```

    mlflow    : 3.14.0
    torch     : 2.13.0
    lightning : 2.6.5


## Part A — The Lightning way (autolog works)

We build a tiny classifier on synthetic data so it runs fast on CPU. The key line is `mlflow.autolog()`. It detects Lightning and logs metrics, params, and checkpoints during `trainer.fit()`.


```python
import torch
from torch import nn
from torch.utils.data import TensorDataset, DataLoader
import lightning as L

# Synthetic 2-class dataset (fast, CPU-friendly)
torch.manual_seed(42)
N, D = 1000, 20
X = torch.randn(N, D)
w = torch.randn(D, 1)
y = (X @ w + 0.1 * torch.randn(N, 1) > 0).long().squeeze()
train_loader = DataLoader(TensorDataset(X, y), batch_size=64, shuffle=True)
```


```python
class LitClassifier(L.LightningModule):
    def __init__(self, in_dim=20, hidden=32, lr=1e-3):
        super().__init__()
        self.save_hyperparameters()   # Lightning records these; autolog picks them up
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden), nn.ReLU(), nn.Linear(hidden, 2)
        )
        self.loss_fn = nn.CrossEntropyLoss()

    def forward(self, x):
        return self.net(x)

    def training_step(self, batch, batch_idx):
        x, y = batch
        logits = self(x)
        loss = self.loss_fn(logits, y)
        acc = (logits.argmax(1) == y).float().mean()
        self.log("train_loss", loss)   # surfaced by autolog
        self.log("train_acc", acc)
        return loss

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=self.hparams.lr)
```


```python
mlflow.set_tracking_uri("sqlite:///mlflow.db")
mlflow.set_experiment("pytorch-lightning-autolog-demo")
mlflow.autolog()   # detects Lightning; logs metrics, params, checkpoints

model = LitClassifier(in_dim=D, hidden=32, lr=1e-3)
trainer = L.Trainer(max_epochs=5, enable_progress_bar=True, logger=False)
trainer.fit(model, train_loader)   # run tracked automatically
```

    2026/07/20 23:56:57 INFO mlflow.tracking.fluent: Experiment with name 'pytorch-lightning-autolog-demo' does not exist. Creating a new experiment.


    2026/07/20 23:56:57 INFO mlflow.tracking.fluent: Autologging successfully enabled for lightning.


    2026/07/20 23:56:57 INFO mlflow.tracking.fluent: Autologging successfully enabled for pytorch_lightning.


    INFO:pytorch_lightning.utilities.rank_zero:GPU available: True (mps), used: True


    INFO:pytorch_lightning.utilities.rank_zero:TPU available: False, using: 0 TPU cores


    INFO:pytorch_lightning.utilities.rank_zero:💡 Tip: For seamless cloud logging and experiment tracking, try installing [litlogger](https://pypi.org/project/litlogger/) to enable LitLogger, which logs metrics and artifacts automatically to the Lightning Experiments platform.


    2026/07/20 23:56:58 INFO mlflow.utils.autologging_utils: Created MLflow autologging run with ID '4fe3c917488d497387aa050fa50d6a91', which will track hyperparameters, performance metrics, model artifacts, and lineage information for the current pytorch workflow


    INFO:pytorch_lightning.utilities.rank_zero:💡 Tip: For seamless cloud uploads and versioning, try installing [litmodels](https://pypi.org/project/litmodels/) to enable LitModelCheckpoint, which syncs automatically with the Lightning model registry.


    
      | Name    | Type             | Params | Mode  | FLOPs
    -------------------------------------------------------------
    0 | net     | Sequential       | 738    | train | 0    
    1 | loss_fn | CrossEntropyLoss | 0      | train | 0    
    -------------------------------------------------------------
    738       Trainable params
    0         Non-trainable params
    738       Total params
    0.003     Total estimated model params size (MB)
    5         Modules in train mode
    0         Modules in eval mode
    0         Total Flops


    /Users/mac/Documents/admin/AgenticCraft/mlflow-tutorials/tutorial_2_autolog_in_mlflow/.venv/lib/python3.12/site-packages/lightning/pytorch/utilities/_pytree.py:21: `isinstance(treespec, LeafSpec)` is deprecated, use `isinstance(treespec, TreeSpec) and treespec.is_leaf()` instead.
    /Users/mac/Documents/admin/AgenticCraft/mlflow-tutorials/tutorial_2_autolog_in_mlflow/.venv/lib/python3.12/site-packages/lightning/pytorch/trainer/connectors/data_connector.py:434: The 'train_dataloader' does not have many workers which may be a bottleneck. Consider increasing the value of the `num_workers` argument` to `num_workers=7` in the `DataLoader` to improve performance.



    Training: |          | 0/? [00:00<?, ?it/s]


    2026/07/20 23:57:01 WARNING mlflow.utils.checkpoint_utils: Checkpoint logging is skipped, because checkpoint 'save_best_only' config is True, it requires to compare the monitored metric value, but the provided monitored metric value is not available.


    2026/07/20 23:57:01 WARNING mlflow.utils.checkpoint_utils: Checkpoint logging is skipped, because checkpoint 'save_best_only' config is True, it requires to compare the monitored metric value, but the provided monitored metric value is not available.


    2026/07/20 23:57:01 WARNING mlflow.utils.checkpoint_utils: Checkpoint logging is skipped, because checkpoint 'save_best_only' config is True, it requires to compare the monitored metric value, but the provided monitored metric value is not available.


    2026/07/20 23:57:01 WARNING mlflow.utils.checkpoint_utils: Checkpoint logging is skipped, because checkpoint 'save_best_only' config is True, it requires to compare the monitored metric value, but the provided monitored metric value is not available.


    2026/07/20 23:57:01 WARNING mlflow.utils.checkpoint_utils: Checkpoint logging is skipped, because checkpoint 'save_best_only' config is True, it requires to compare the monitored metric value, but the provided monitored metric value is not available.


    INFO:pytorch_lightning.utilities.rank_zero:`Trainer.fit` stopped: `max_epochs=5` reached.


    2026/07/20 23:57:01 WARNING mlflow.pytorch: Saving pytorch model by Pickle or CloudPickle format requires exercising caution because these formats rely on Python's object serialization mechanism, which can execute arbitrary code during deserialization. The recommended safe alternative is to set `serialization_format` to 'pt2' to save the PyTorch model using the safe graph model format.


    2026/07/20 23:57:02 INFO mlflow.utils.uv_utils: Detected uv project: found uv.lock and pyproject.toml in /Users/mac/Documents/admin/AgenticCraft/mlflow-tutorials/tutorial_2_autolog_in_mlflow


    2026/07/20 23:57:02 INFO mlflow.utils.environment: Detected uv project at /Users/mac/Documents/admin/AgenticCraft/mlflow-tutorials/tutorial_2_autolog_in_mlflow. Attempting to export requirements via 'uv export'.


    2026/07/20 23:57:02 INFO mlflow.utils.uv_utils: Exported 177 dependencies via uv


    2026/07/20 23:57:02 INFO mlflow.utils.environment: Successfully exported 177 requirements from uv project. Skipping package capture based inference.


    2026/07/20 23:57:02 WARNING mlflow.utils.environment: Failed to resolve installed pip version. ``pip`` will be added to conda.yaml environment spec without a version specifier.


## Part B — The raw PyTorch loop (manual logging)

If you don't use Lightning, autolog has nothing to hook into. You wrap the run yourself and call `mlflow.log_metric()` where it matters. More code, same destination.


```python
net = nn.Sequential(nn.Linear(D, 32), nn.ReLU(), nn.Linear(32, 2))
opt = torch.optim.Adam(net.parameters(), lr=1e-3)
loss_fn = nn.CrossEntropyLoss()

mlflow.autolog(disable=True)  # make the contrast explicit: autolog off here

with mlflow.start_run(run_name="raw-loop-manual"):
    mlflow.log_params({"hidden": 32, "lr": 1e-3, "epochs": 5, "framework": "raw-pytorch"})
    for epoch in range(5):
        running = 0.0
        for xb, yb in train_loader:
            opt.zero_grad()
            loss = loss_fn(net(xb), yb)
            loss.backward()
            opt.step()
            running += loss.item()
        avg = running / len(train_loader)
        mlflow.log_metric("train_loss", avg, step=epoch)   # you log, by hand
        print(f"epoch {epoch}  loss {avg:.4f}")
```

    epoch 0  loss 0.7012
    epoch 1  loss 0.6524
    epoch 2  loss 0.6080
    epoch 3  loss 0.5628
    epoch 4  loss 0.5129


## Open the MLflow UI

```bash
mlflow ui --backend-store-uri sqlite:///mlflow.db   # macOS: add --port 5001 if 5000 is taken by AirPlay
```

Open the experiment and compare:
- The **Lightning** run: metrics, params, and checkpoints appeared with no logging code.
- The **raw-loop** run: only the metrics you logged by hand.

**Takeaway:** autolog for PyTorch is really a Lightning feature. Reach for Lightning when you want zero-config; use manual `log_metric()` when you're on a custom loop.

## Recap

- `mlflow.autolog()` + PyTorch Lightning = zero-config tracking.
- Raw PyTorch loops need manual `mlflow.log_metric()` / `log_params()`.
- Same UI, same comparison, different amount of code.

**Next:** Notebook 3 crosses into GenAI, where the unit of work is a *trace*, not a `fit()`.
