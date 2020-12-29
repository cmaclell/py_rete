# py_rete

[![image][]][travis] [![image][coveralls-badge]][coveralls-repo]

## Introduction

The py_rete project aims to implement a Rete engine in native python. This
system is built using one the description of the Rete algorithms provided by
[Doorenbos (1995)][doorenbos]. It also makes heavy use of ideas from the
[Experta project][experta] (although no code is used from this project as it
utilizes an LGPL license).

The purpose of this system is to support basic expert / production system AI
capabilities in a way that is easy to integrate with other Python based AI/ML
systems.

## Installation

This package is installable via pip with the following command:
`pip install -U py_rete`.

It can also be installed directly from GitHub with the following command:
`pip install -U git+https://github.com/cmaclell/py_rete@master`

## The Basics

The two high-level structures to support reasoning with py_rete are **facts**
and **productions**. 

### Facts

Facts represent the basic units of knowledge that the productions match over.
Here are a few examples of facts and how they work.

1. *Facts* are a subclass of dict, so you can treat them similar to dictionaries.

```python
>>> f = Fact(a=1, b=2)
>>> f['a']
1
```

2. Similar to dictionaries, *Facts* do not maintain an internal order of items.

```python
>>> Fact(a=1, b=2)
Fact(b=2, a=1)
```

3. *Facts* extend dictionarieis, so they also support values without keys.

```python
>>> f = Fact('a', 'b', 'c')
>>> f[0]
'a'
```

4. *Facts* can support mixed positional and named arguments, but positional
   must come before named and named arguments do not get positional references.

```python
>>> f = Fact('a', 'b', c=3, d=4)
>>> f[0]
'a'
>>> f['c']
3
```

### Productions

Similar to Experta's rules, *Productions* are functions that are decorated with
conditions that govern when they execute and bind the arguments necessary for
their execution.

Productions have two components:
* Conditions, which are essentially facts that can pattern matching variables.
* A Function, which is executed for each rule match, with the arguments to the
  function being passed the bindings from pattern matching variables.

Here is an example of a simple *Production* that binds with all *Facts* that
have the color red and prints 'There is something red present':

```python
@Production(Fact(color='red'))
def something_red_present():
    print("There is something red present")
```


[experta]: https://github.com/nilp0inter/experta
[doorenbos]: http://reports-archive.adm.cs.cmu.edu/anon/1995/CMU-CS-95-113.pdf
[image]: https://travis-ci.com/cmaclell/py_rete.svg?branch=master
[travis]: https://travis-ci.com/cmaclell/py_rete
[coveralls-badge]: https://coveralls.io/repos/github/cmaclell/py_rete/badge.svg?branch=master
[coveralls-repo]: https://coveralls.io/github/cmaclell/py_rete?branch=master
