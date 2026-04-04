"""AVL audit, stress mode, and rebalance operations."""


class AuditService:
	"""Encapsulates AVL stress mode, audit, and global rebalance logic."""

	def enable_stress_mode(self, avl):
		avl.enable_stress_mode()
		return {"stressMode": True}

	def disable_stress_mode(self, avl):
		avl.disable_stress_mode()
		return {"stressMode": False}

	def audit_avl(self, avl):
		if not avl.stress_mode:
			return {"error": "La auditoría solo está disponible en modo estrés."}

		return avl.audit_avl()

	def global_rebalance(self, avl):
		if not avl.stress_mode:
			return {"error": "El rebalanceo global solo está disponible en modo estrés."}

		return avl.global_rebalance()
