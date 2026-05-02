import numpy as np
import torch
import torch.nn as nn


class FatigueLSTM(nn.Module):

    def __init__(self, input_size=1, hidden_size=32, num_layers=1):
        super(FatigueLSTM, self).__init__()

        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):

        out, _ = self.lstm(x)
        out = out[:, -1, :]
        out = self.fc(out)

        return out


class FatiguePredictor:

    def __init__(self, sequence_length=30):

        self.sequence_length = sequence_length
        self.history = []

        self.model = FatigueLSTM()
        self.model.eval()

    def update(self, score):

        self.history.append(score)

        if len(self.history) > self.sequence_length:
            self.history.pop(0)

    def predict(self):

        if len(self.history) < self.sequence_length:
            return None

        seq = np.array(self.history).reshape(1, self.sequence_length, 1)

        tensor = torch.FloatTensor(seq)

        with torch.no_grad():
            pred = self.model(tensor).item()

        pred = max(0, min(100, pred))

        return int(pred)