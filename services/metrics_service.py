"""Metrics and summary builders for AVL/BST tree state."""

from persistence.json_serializer import JsonSerializer


class MetricsService:
	"""Build metrics and standardized summaries from current tree state."""

	def get_metrics(self, avl, critical_depth):
		root = avl.get_root()
		has_root = root is not None

		return {
			"height": avl.calculate_height(root) + 1 if has_root else 0,
			"totalNodes": avl.count_nodes(),
			"leafCount": avl.count_leaves(),
			"rotations": avl.get_rotation_stats(),
			"massCancellations": avl.mass_cancellations,
			"stressMode": avl.stress_mode,
			"criticalDepth": critical_depth,
			"bfs": [flight.to_dict() for flight in avl.get_breadth_first_list()],
			"dfs": [flight.to_dict() for flight in avl.get_pre_order_list()],
			"inorder": [flight.to_dict() for flight in avl.get_in_order_list()],
			"postorder": [flight.to_dict() for flight in avl.get_post_order_list()],
		}

	def get_avl_summary(self, avl):
		root = avl.get_root()

		return {
			"raiz": root.get_value().get_code() if root is not None else None,
			"profundidad": avl.calculate_height(root) + 1 if root is not None else 0,
			"cantidadHojas": avl.count_leaves(),
			"totalNodos": avl.count_nodes(),
			"rotaciones": avl.get_rotation_stats(),
		}

	def get_bst_summary(self, bst):
		root = bst.get_root()

		return {
			"raiz": root.get_value().get_code() if root is not None else None,
			"profundidad": bst.calculate_height(root) + 1 if root is not None else 0,
			"cantidadHojas": bst.count_leaves(),
			"totalNodos": bst.count_nodes(),
		}

	def get_tree_response(self, avl):
		return {
			"tree": JsonSerializer.serialize_tree(avl.get_root()),
			"properties": self.get_avl_summary(avl),
		}
