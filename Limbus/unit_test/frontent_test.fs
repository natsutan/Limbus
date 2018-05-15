module frontent_test

open NUnit.Framework
open Token


[<TestFixture>]
type Test_Token () =

    [<Test>]
    member this.TestToken() =
        let a : Token = { Val = "aaa" ;}
        Assert.AreEqual(a.Val, "aaa")
        Assert.IsTrue(true)

 
