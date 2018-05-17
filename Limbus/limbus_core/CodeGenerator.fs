module CodeGenerator

open common

[<Class>]
type CodeGenerator(iCode : iCode, symTab : SymTab) = 
    let mutable iCode = iCode
    let mutable symTab = symTab
    member this.message_handler = MessegeHandller()    
    member val instruction_count = 0 with set, get
    
    interface  MessageProducer with 
         member this.add_message_listener(ml: MessageListener) : unit = 
             this.message_handler.add_message_listener(ml)
         member this.remove_message_listener(ml : MessageListener) : unit = 
             this.message_handler.remove_message_listener(ml)
         member this.send_message(m : Message) : unit = 
             this.message_handler.send_message(m)
         
    member this.send_message(m : Message) : unit = 
        this.message_handler.send_message(m)    
    
    member this.lprocess( iCode : iCode, symTab : SymTab) : unit =
        this.instruction_count <- 0
        //sendmessage
        let ms = string(this.instruction_count)
        let m = {msg_type = COMPILER_SUMMARY ; body = MSG ms;}
        this.send_message(m)
        
     
    