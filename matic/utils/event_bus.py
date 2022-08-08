from __future__ import annotations

from typing import Any, Callable

# export interface IEventBusPromise<T> extends Promise<T> {
#     on(event: str, cb: Callable[..., Any])
#     emit(event: str, ...args)
#     destroy()
# }

# export const eventBusPromise = function <T>(executor: (resolve: (value?: T | PromiseLike<T>) => void, reject: (reason?: any) => void) => void) {
#     const promise: IEventBusPromise<T> = new Promise(executor) as any
#     const eventBus = new EventBus()
#     promise.on = eventBus.on.bind(eventBus)
#     promise.emit = eventBus.emit.bind(eventBus)
#     return promise
# }


class EventBus:
    def __init__(self, ctx: Something | None = None):
        self._ctx = ctx
        self._events: dict[str, list[Callable[..., Any]]] = {}

    def on(self, event: str, cb: Callable[..., Any]):
        self._events.setdefault(event, []).append(cb)
        return self

    def off(self, event: str, cb: Callable[..., Any] | None = None):
        if not self._events.get(event, []):
            return

        if cb:
            self._events[event] = [e for e in self._events[event] if e != cb]
        else:
            self._events[event] = []

    def emit(self, event: str, *args: Any) -> list[Any]:
        return [cb(self._ctx, *args) for cb in self._events.get(event, [])]

    # destroy() {
    #     self._events = null
    #     self._ctx = null
    # Can be safely omitted
    # }
