# DS-Homework 1

### Info

* **Group member**:  `Andro Lominadze, Kadir Aktas, Xatia Kilanava, Shan Wu`
* **File structure**: We have two documental files, this `README.md` is for understand to use homework application and knows our file structure. Another document is `Implementation file`, that contains all the details of our homework. In this folder, we have:
    - `client-main`(to start client), 
    - `client_protocol`(protocol constants), 
    - `server_main`(to start server), 
    - `server_protocol`(server process), 
    - `sudoku_generator`(to generate a sudoku game), 
    - `base.txt`(file needed to generate sudoku), 
    - `Sudoku folder`(needed to generate sudoku). 
* **About the work**: We divided our work in this homework. Protocol is defined by all of us together. In implementation, `Andro` is for server main, `Xatia` is for server process, `Shan` is for client with UI, `Kadir` is for functions we all need in server and client.
* **About sudoku generator**: It's from the [Github sudoku-generator](https://github.com/RutledgePaulV/sudoku-generator/blob/master/sudoku_generator.py). Thanks for the help from this generator. After modified, sudoku generator can provide the data we want.

### Usage

* **Server**: Just run it, it will run on default server address and port. Or you can follow this usage:
    - `server_main.py [-h] [-v] [-a ADDRESS] [-p PORT]`.
* **Client**: Before run it, make sure you have installed python package `Tkinter`. Then you can simply run it. All the instructions is on the UI interface, it's easy to understand what is going on on client. For more detail information about User Interface please check the document `Implementation of Sudoku Application.docx`, in `client` part.

* **What works**: 
    - all basic funtion works
* **What problem**:
    - our server address and port need to write correctly at once, if you type wrong, you may need to reopen the client
    - it happened many times when you are doing right, just normal operation will cause the UI freezed, you can only restart client.
    - when other player joins the existing game, maybe his Sudoku and score board is not real data, after other user input a right number, it will be updated automatically.
    

