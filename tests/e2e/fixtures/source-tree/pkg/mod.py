class Greeter:
    def hello(self):
        def inner():
            return 1

        return inner()


def top_level():
    return 2
