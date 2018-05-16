module Parser
open MessageIF
open common
open Token
open Scanner

[<AbstractClass>]
type Parser(scanner : Scanner) = 
    member this.message_handler = MessegeHandller()    

    interface  MessageProducer with 
        member this.add_message_listener(ml: MessageListener) : unit = 
            this.message_handler.add_message_listener(ml)
        member this.remove_message_listener(ml : MessageListener) : unit = 
            this.message_handler.remove_message_listener(ml)
        member this.send_message(m : Message) : unit = 
            this.message_handler.send_message(m)


    member this.symTab = null 
    member this.iCode = null 
    member this.scanner = scanner 
    
    abstract member parse : unit -> unit
    abstract member get_error_count : unit -> int 
    
    member this.current_token() : Token = this.scanner.cuurent_token()
        
    member this.next_token() : Token = this.scanner.next_token()
    
    member this.send_message(m : Message) : unit = 
        this.message_handler.send_message(m)
