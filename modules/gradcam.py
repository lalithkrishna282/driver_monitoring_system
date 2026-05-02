import torch
import numpy as np


class GradCAM:

    def __init__(self, model, target_layer=None):

        self.model = model
        self.model.eval()

        self.gradients = None
        self.activations = None

        # NEW: device detection
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        if target_layer is None:
            for module in reversed(list(self.model.modules())):
                if isinstance(module, torch.nn.Conv2d):
                    self.target_layer = module
                    break
        else:
            self.target_layer = target_layer

        # hooks
        self.target_layer.register_forward_hook(self.save_activation)
        self.target_layer.register_full_backward_hook(self.save_gradient)

    def save_activation(self, module, input, output):
        self.activations = output

    def save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0]

    def generate(self, input_tensor):

        # NEW: ensure tensor is on correct device
        input_tensor = input_tensor.to(self.device)

        output = self.model(input_tensor)

        if isinstance(output, tuple):
            output = output[0]

        # NEW: safety check
        if output is None:
            return np.zeros((48,48), dtype=np.float32)

        class_idx = torch.argmax(output)

        self.model.zero_grad()

        # NEW: ensure gradients enabled
        with torch.enable_grad():
            output[0, class_idx].backward(retain_graph=True)

        # NEW: safety checks
        if self.gradients is None or self.activations is None:
            return np.zeros((48,48), dtype=np.float32)

        gradients = self.gradients.detach().cpu().numpy()[0]
        activations = self.activations.detach().cpu().numpy()[0]

        weights = np.mean(gradients, axis=(1, 2))

        cam = np.zeros(activations.shape[1:], dtype=np.float32)

        for i, w in enumerate(weights):
            cam += w * activations[i]

        cam = np.maximum(cam, 0)

        # NEW: normalization protection
        max_val = cam.max()
        if max_val != 0:
            cam = cam / max_val

        # NEW: resize safety
        if cam.shape[0] == 0 or cam.shape[1] == 0:
            return np.zeros((48,48), dtype=np.float32)

        return cam