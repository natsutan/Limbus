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
    