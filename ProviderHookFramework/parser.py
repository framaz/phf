from phfsystem import PHFSystem

if __name__ == "__main__":
    phfsys = PHFSystem()
    phfsys.import_hook_sources("hooks")
    phfsys.import_provider_sources("providers")

    #   hook = BasicPrintHook()
    #   provider = DummyBlocking()
    #   provider.add_hook(hook)
    #    phfsys.add_content_provider(provider)

    phfsys.start()
