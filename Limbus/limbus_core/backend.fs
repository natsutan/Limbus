module backend
open common


[<AbstractClass>]
type Backend(iCode : iCode, symTab : SymTab) = 
    let mutable iCode = iCode
    let mutable symTab = symTab

    member this.message_handler = MessegeHandller()    
    
    interface  MessageProducer with 
        member this.add_message_listener(ml: MessageListener) : unit = 
            this.message_handler.add_message_listener(ml)
        member this.remove_message_listener(ml : MessageListener) : unit = 
            this.message_handler.remove_message_listener(ml)
        member this.send_message(m : Message) : unit = 
            this.message_handler.send_message(m)
            
    abstract member process : iCode -> SymTab -> unit
    

[<Class>]
type Interpreter(iCode : iCode, symTab : SymTab) = 
    let mutable iCode = iCode
    let mutable symTab = symTab
    
    member this.message_handler = MessegeHandller()    
    member val execution_count = 0 with set, get
    member val runtime_errres = 0 with set, get
    
    
    interface  MessageProducer with 
         member this.add_message_listener(ml: MessageListener) : unit = 
             this.message_handler.add_message_listener(ml)
         member this.remove_message_listener(ml : MessageListener) : unit = 
             this.message_handler.remove_message_listener(ml)
         member this.send_message(m : Message) : unit = 
             this.message_handler.send_message(m)
         
    member this.send_message(m : Message) : unit = 
        this.message_handler.send_message(m)
         
         
    member this.lprocess(iCode : iCode, symTab : SymTab) : unit =
        this.execution_count <- 0
        this.runtime_errres <- 0
        //sendmessage
        let es = string(this.execution_count)
        let rs = string(this.runtime_errres)
        
        let m = {msg_type = INTERPRETER_SUMMARY ; body = MSGS [es ; rs];}
        this.send_message(m)
               
                     
