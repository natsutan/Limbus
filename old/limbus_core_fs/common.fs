module common


// Message I/F
type MessageType = DUMMY | SOURCE_LINE | SYNTAX_ERROR | PARSER_SUMMARY | INTERPRETER_SUMMARY | COMPILER_SUMMARY | MISCELLANEOUS | MSG_TOKEN | ASSIGN |  FETCH | BREAKPOINT | RUNTIME_ERROR | CALL |  RETURN
type MessageBody = MSG of string | MSGS of List<string>
                   
type Message = {msg_type : MessageType;  body : MessageBody }

type MessageListener = 
    interface
        abstract name : string
        abstract message_received : Message -> unit
    end
             
type MessageProducer = 
    interface
        abstract add_message_listener : MessageListener -> unit
        abstract remove_message_listener : MessageListener -> unit
        abstract send_message : Message -> unit
    end
         
[<Class>]
type MessegeHandller() =
    let mutable msg = { msg_type = DUMMY; body = MSG ""}
    let mutable listeners : List<MessageListener> = []
    
    member this.add_message_listener(l : MessageListener) : unit =
        listeners <- List.append listeners [l]
        
    member this.remove_message_listener(l : MessageListener) : unit =
        listeners <- List.filter (fun e -> e.name <> l.name) listeners 
        
    member this.send_message(m : Message) : unit =
        msg <- m
        this.notify_listeners()
        
    member this.notify_listeners() : unit = 
        for l in listeners do l.message_received(msg)
        


type iCode = int
type SymTab = int


