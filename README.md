# Description
This is a project was built as part of a university assignment to design a truss bridge at as low a price as possible. It accomplishes this using a pseudo-genetic algorithm, generating a pool of mostly random starting truss structures, selecting the top few best performers, and generating variations upon those in hopes of finding a cheaper truss. 

# Usage
To use this program, first ensure you have all the dependencies installed via pip. Then, simply run main.py to generate a pool and view the results of training. The top performer of each generation of trusses will be saved in the truss_checkpoints directory as a pickled python object of the Truss class (available in truss.py).

# Screenshots
todo

# License

MIT License

Copyright (c) 2023 Owen Zephyr Grimm

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.