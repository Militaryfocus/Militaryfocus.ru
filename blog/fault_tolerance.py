"""
Алиас для системы отказоустойчивости
Импортирует все классы из fault_tolerance_perfect.py для обратной совместимости
"""

# Импорт всех классов из идеального модуля
from blog.fault_tolerance_perfect import *

# Экспорт основных классов для совместимости
fault_tolerant_system = perfect_fault_tolerance_system

__all__ = [
    'fault_tolerant_system', 'init_fault_tolerance', 'shutdown_fault_tolerance'
]