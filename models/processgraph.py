from  .graphbuilder import GraphBuilder
import collections

class Processgraph:

    def __init__(self, node_id:str=None, builder:GraphBuilder=None):

        if not builder:
            builder = GraphBuilder()

        self.builder = builder
        self.node_id = node_id
        self.graph = builder.processes
        self.REDUCERS = ["min", "max", "mean", "median", "count"]

    def add_process(self, process_id, arguments):
        """
        Returns a new Processgraph with the additional process (process_id) using the dictionary of arguments (args)
        Detects if the process is a reducer
        :param process_id: String, Process Id of the added process.
        :param args: Dict, Arguments of the process.
        :return: processgraph: Instance of the Processgraph class
        """
        if process_id in self.REDUCERS:
            return self._reduce_time(process_id)
        else:
            return self.graph_add_process(process_id, arguments)

    def _reduce_time(self, reduce_function = "max"):
        """
        Add a time reducer to the process graph, returns the process graph with the reducer
        :param reduce_function: String, Reducer function one of Processgraph.REDUCERS
        :return: processgraph: Instance of the Processgraph class
        """
        process_id = 'reduce'

        args = {
            'data': {'from_node': self.node_id},
            'dimension': 'temporal',
            'reducer': {
                'callback': {
                    'r1': {
                        'arguments': {
                            'data': {
                                'from_argument': 'data'
                            }
                        },
                        'process_id': reduce_function,
                        'result': True
                    }
                }
            }
        }

        return self.graph_add_process(process_id, args)

    def load_collection(self, arguments):
        """
        Sets the collection of the processgraph
        id and a dictionary of arguments
        :param collection_id: String, Collection Id.
        """
        self.builder = GraphBuilder()

        #collection_id = None
        #ex = None
        #tex = None
        #bands = None

        process_id = 'load_collection'

        #arguments = collections.OrderedDict({
        #    'id': collection_id,
        #    'spatial_extent': ex,
        #    'temporal_extent': tex,
        #    'bands': bands
        #})
        self.node_id = self.builder.process(process_id, arguments)
        self.graph = self.builder.processes


    def graph_add_process(self, process_id, args):
        """
        Returns a new Processgraph with the additional process (process_id) using the dictionary of arguments (args)
        :param process_id: String, Process Id of the added process.
        :param args: Dict, Arguments of the process.
        :return: processgraph: Instance of the Processgraph class
        """
        newbuilder = GraphBuilder(self.builder.processes)

        #args["from_node"] = self.node_id

        id = newbuilder.process(process_id, args)

        newProcessgraph = Processgraph(id, newbuilder)

        return newProcessgraph