from aioconsole import ainput

from commandinput import AbstractCommandInput


class ConsoleDebugInput(AbstractCommandInput):
    async def get_command(self):
        input_command = await ainput("Enter site name:\n")
        input_array = input_command.split(" ")
        res = dict()

        # hello yandereDev
        if input_array[0] == "new_hook":
            res["type"] = "new_hook"
            res["target_provider_num"] = int(input_array[2])
            res["target_class"] = input_array[1]
            pos_args, keyword_args = self.get_arguments(input_array[3:])
            res["positionals"] = pos_args
            res["keywords"] = keyword_args

        elif input_array[0] == "new_provider":
            res["type"] = "new_provider"
            res["target_class"] = input_array[1]
            pos_args, keyword_args = self.get_arguments(input_array[2:])
            res["positionals"] = pos_args
            res["keywords"] = keyword_args

        elif input_array[0] == "list_providers":
            res["type"] = "list_providers"

        elif input_array[0] == "list_hooks":
            res["type"] = "list_hooks"
            res['target_provider_num'] = int(input_array[1])

        return res

    def get_arguments(self, input_array):
        positional_arguments = []
        keyword_arguments = {}
        for argument in input_array:
            eq_position = argument.find("=")
            if eq_position != -1:
                keyword = argument[0:eq_position]
                value = argument[eq_position + 1:]
                keyword_arguments[keyword] = value
            else:
                positional_arguments.append(argument)
        return positional_arguments, keyword_arguments

    async def output_command_result(self, command_result):
        print(str(command_result))
