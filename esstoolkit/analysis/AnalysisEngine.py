class AnalysisEngine:
    class AnalysisEngineError(Exception):
        """ Generic Exception raised when the engine errors"""
        pass

    class AnalysisResults:
        """ Stores results from the analysis for passing around"""
        def __init__(self, attributes, types, values, coords):
            self.attributes = attributes
            self.types = types
            self.values = values
            self.coords = coords
