import socket


class TestUtils:

    @staticmethod
    def disable_socket(monkeypatch):
        """Disable socket.socket and socket.create_connection."""

        def guard(*args, **kwargs):
            raise RuntimeError("Network access not allowed during this test.")

        monkeypatch.setattr(socket, "socket", guard)
        monkeypatch.setattr(socket, "create_connection", guard)

    @staticmethod
    def enable_socket(monkeypatch):
        """Restore socket.socket and socket.create_connection to their original state."""
        monkeypatch.undo()
