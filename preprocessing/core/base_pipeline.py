from abc import ABC, abstractmethod

class BasePipeline(ABC):

    @abstractmethod
    def load_raw(self, filepath):
        pass

    @abstractmethod
    def pc3_filter(self, data):
        pass

    @abstractmethod
    def pooling(self, data):
        pass

    @abstractmethod
    def cwt(self, data):
        pass

    @abstractmethod
    def normalize(self, tensor):
        pass

    @abstractmethod
    def build_tensor(self, data):
        pass
