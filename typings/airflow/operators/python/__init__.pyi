from typing import Any, Callable, Protocol

from ... import DAG


class _PythonCallable(Protocol):
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


class BaseOperator:
    task_id: str

    def __init__(self, *, task_id: str, **kwargs: Any) -> None: ...

    def execute(self, context: dict[str, Any]) -> Any: ...


class PythonOperator(BaseOperator):
    def __init__(
        self,
        *,
        task_id: str,
        python_callable: Callable[..., Any],
        provide_context: bool = ...,
        dag: DAG | None = ...,
        **kwargs: Any,
    ) -> None: ...

    def __rshift__(self, other: "PythonOperator | list[PythonOperator]") -> "PythonOperator | list[PythonOperator]": ...
    def __lshift__(self, other: "PythonOperator | list[PythonOperator]") -> "PythonOperator | list[PythonOperator]": ...
    def __rrshift__(self, other: "PythonOperator | list[PythonOperator]") -> "PythonOperator | list[PythonOperator]": ...
    def __rlshift__(self, other: "PythonOperator | list[PythonOperator]") -> "PythonOperator | list[PythonOperator]": ...


__all__ = ["PythonOperator", "BaseOperator"]


