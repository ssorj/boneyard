require "json"

module Lowboy
    namespaces = {
        "proton" => "Proton",
    }

    class Executor
        def initialize
            @operations = Array.new
            @variables = Hash.new
        end

        def unmarshal(input)
            for line in input.each_line
                op = Operation.new
                op.unmarshal(line)
                
                @operations.push(op)
            end
        end

        def execute
            for op in @operations
                op.execute(@variables)
            end
        end
    end

    class Operation
        def initialize
            @type = nil
            @id = nil
            @namespace = nil
            @name = nil
            @arguments = nil
        end

        def unmarshal(string)
            data = JSON::load(string)

            @type = data["type"]
            @id = data["id"]
            @namespace = data["namespace"]
            @name = data["name"]
            @arguments = data["arguments"]
        end

        def execute(variables)
            if @type == "method-call"
                obj = @variables[:@id]
                meth = obj.send(@name) # XXX args
            elsif @type == "constructor-call"
                puts namespaces, @namespace
                mod = eval(Lowboy::namespaces[:@namespace])
                cls = mod.const_get(@name)
                obj = cls.new # XXX args

                @variables[:@id] = obj
            end
        end
    end
end
