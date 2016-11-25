class _ProfiledThread(_threading.Thread):
    def run(self):
        import cProfile
        prof = cProfile.Profile()

        try:
            return prof.runcall(self.profiled_run)
        finally:
            prof.dump_stats("{}.profile".format(self.ident))
