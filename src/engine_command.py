from search_options import SearchOptions


class EngineCommand:
    def __init__(
        self,
        search_options: SearchOptions | None = None,
        engine_stop: bool = False,  # noqa: FBT001, FBT002
        engine_quit: bool = False,  # noqa: FBT001, FBT002
    ) -> None:
        """
        Command for engine.
        :param search_options: optional search options for calculation
        :param engine_stop: command to stop calculation and wait for a new command
        :param engine_quit: stop calculation and quit the engine process
        """
        self.search_options = search_options or SearchOptions()
        self.stop = engine_stop
        self.quit = engine_quit
