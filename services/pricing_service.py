"""Business pricing and metadata recalculation for AVL nodes."""


class PricingService:
	"""Encapsulates critical depth, rentability, and metadata recalculation logic."""

	def _code_sort_key(self, code):
		"""
		Build a robust comparison key for flight codes.

		Preference order:
		1) Numeric part when present (higher is considered larger code).
		2) Lexicographic fallback for non-numeric or tied numeric values.
		"""
		code_text = str(code)
		digits = "".join(ch for ch in code_text if ch.isdigit())

		if digits:
			return (1, int(digits), code_text)

		return (0, -1, code_text)

	def set_critical_depth(self, avl, depth):
		try:
			depth_value = int(depth)
		except (ValueError, TypeError):
			return {"error": "Profundidad crítica inválida."}

		self.recalculate_all_metadata(avl, depth_value)
		return depth_value

	def eliminate_least_profitable(self, avl):
		if avl.get_root() is None:
			return {"error": "El árbol está vacío."}

		target = self.find_least_profitable_node(avl)
		if target is None:
			return {"error": "No se encontró un nodo candidato."}

		return {
			"code": target.get_value().get_code(),
			"rentability": target.get_value().rentability,
		}

	def find_least_profitable_node(self, avl):
		candidates = []
		self.collect_rentability(avl.get_root(), candidates)

		if len(candidates) == 0:
			return None

		best = candidates[0]

		for candidate in candidates[1:]:
			if candidate[0] < best[0]:
				best = candidate
			elif candidate[0] == best[0]:
				if candidate[1] > best[1]:
					best = candidate
				elif candidate[1] == best[1]:
					if self._code_sort_key(candidate[2]) > self._code_sort_key(best[2]):
						best = candidate

		return best[3]

	def collect_rentability(self, node, result):
		if node is None:
			return

		flight = node.get_value()
		result.append((
			flight.rentability,
			flight.depth,
			flight.code,
			node,
		))

		self.collect_rentability(node.get_left_child(), result)
		self.collect_rentability(node.get_right_child(), result)

	def recalculate_all_metadata(self, avl, critical_depth):
		self.recalculate_metadata_from_node(avl, avl.get_root(), 0, critical_depth)

	def recalculate_metadata_from_node(self, avl, node, depth, critical_depth):
		if node is None:
			return

		flight = node.get_value()

		flight.depth = depth
		flight.height = avl.calculate_height(node)
		flight.balance_factor = avl.get_balance_factor(node)

		flight.compute_final_price(critical_depth)
		flight.compute_rentability()

		self.recalculate_metadata_from_node(
			avl,
			node.get_left_child(),
			depth + 1,
			critical_depth,
		)
		self.recalculate_metadata_from_node(
			avl,
			node.get_right_child(),
			depth + 1,
			critical_depth,
		)
