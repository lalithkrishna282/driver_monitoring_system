import torch
import torch.nn as nn

class EyeCNN(nn.Module):

    def __init__(self):
        super(EyeCNN, self).__init__()

        self.conv = nn.Sequential(
            nn.Conv2d(1,16,3,padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(16,32,3,padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2)
        )

        self.fc = nn.Sequential(
            nn.Linear(32*12*12,64),
            nn.ReLU(),
            nn.Linear(64,2)
        )

    def forward(self,x):

        features = self.conv(x)
        out = features.view(features.size(0),-1)
        out = self.fc(out)

        return out, features