from abc import ABC, abstractmethod


class IMaterialRewardEvaluator(ABC):
    @abstractmethod
    def evaluate(self, weight_kg: float, base_multiplier: int) -> int:
        pass


class RecyclableMaterialEvaluator(IMaterialRewardEvaluator):
    def evaluate(self, weight_kg: float, base_multiplier: int) -> int:
        return max(0, round(weight_kg * base_multiplier))


class ContaminatedRejectedEvaluator(IMaterialRewardEvaluator):
    def evaluate(self, weight_kg: float, base_multiplier: int) -> int:
        return 0


class MaterialEvaluatorFactory:
    @staticmethod
    def create(is_contaminated: bool, material_type: str) -> IMaterialRewardEvaluator:
        normalized = material_type.strip().upper()
        if is_contaminated or normalized in {"BASURA", "CONTAMINADO", "RECHAZADO"}:
            return ContaminatedRejectedEvaluator()
        return RecyclableMaterialEvaluator()
