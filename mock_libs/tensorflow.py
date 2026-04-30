"""Mock TensorFlow module for compatibility"""
import numpy as np

class MockLayer:
    def __init__(self, *args, **kwargs):
        self.name = kwargs.get('name', 'layer')
    
    def __call__(self, x):
        return x
    
    @property
    def output(self):
        return MockTensor()

class MockTensor:
    def __init__(self):
        pass
    
    def numpy(self):
        return np.array([0.0])

class MockModel:
    def __init__(self, inputs=None, outputs=None):
        self.inputs = inputs
        self.outputs = outputs
    
    def compile(self, *args, **kwargs):
        pass
    
    def predict(self, x):
        return np.array([0.1])
    
    def save(self, path):
        pass
    
    def load_model(path):
        return MockModel()

class MockSequential:
    def __init__(self, layers=None):
        self.layers = layers or []
    
    def add(self, layer):
        self.layers.append(layer)
    
    def compile(self, *args, **kwargs):
        pass
    
    def predict(self, x):
        return np.array([0.1])

# Mock classes
layers = type('layers', (), {
    'Input': MockLayer,
    'Dense': lambda *args, **kwargs: MockLayer(**kwargs),
    'Dropout': lambda *args, **kwargs: MockLayer(**kwargs),
    'Conv2D': lambda *args, **kwargs: MockLayer(**kwargs),
    'Conv1D': lambda *args, **kwargs: MockLayer(**kwargs),
    'MaxPooling2D': lambda *args, **kwargs: MockLayer(**kwargs),
    'MaxPooling1D': lambda *args, **kwargs: MockLayer(**kwargs),
    'LSTM': lambda *args, **kwargs: MockLayer(**kwargs),
    'Embedding': lambda *args, **kwargs: MockLayer(**kwargs),
    'Flatten': lambda *args, **kwargs: MockLayer(**kwargs),
    'concatenate': lambda x: x[0],
})()

keras = type('keras', (), {
    'Model': MockModel,
    'Sequential': MockSequential,
    'models': type('models', (), {'load_model': MockModel.load_model})(),
})()

def random_normal(shape):
    return np.random.normal(0, 1, shape)

# Version info
__version__ = '2.15.0-mock'
