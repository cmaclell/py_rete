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
and **skills**. 

### Facts

Facts represent the basic units of knowledge that the skills match over.
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

### Skills

Similar to Experta's rules, *Skills* are functions that are decorated with
conditions that govern when they execute and bind the arguments necessary for
their execution.

*Skills* have two components:
* Conditions, which are essentially facts that can pattern matching variables.
* A Function, which is executed for each rule match, with the arguments to the
  function being passed the bindings from pattern matching variables.

Here is an example of a simple *Skills* that binds with all *Facts* that
have the color red and prints 'I found something red':

```python
@Skill(Fact(color='red'))
def alert_something_red():
    print("I found something red")
```

Skills also support logical operators to express more complex conditions.

```python
@Skill(AND(OR(Fact(color='red'),
              Fact(color='blue')),
	   NOT(Fact(color='green'))))
def alert_something_complex():
    print("I found something red or blue without any green present")
```

Bitwise logical operators can be used as shorthand to make composing complex conditions easier.
```python
@Skill((Fact(color='red') | Fact(color='blue')) & ~Fact(color='green'))
def alert_something_complex():
    print("I found something red or blue without any green present")
```

In addition to matching simple facts, pattern matching variables can be used to
match wildcards, ensure variables are consistent across conditions, and to bind
variables for functions.
```python
@Skill(Fact(firstname='Chris', lastname=V('lastname')) &
       Fact(first='John', lastname=V('lastname')))
def found_relatives(lastname):
    print("I found a pair of relatives with the lastname: {}".format(lastname))
```

It is also possible to employ functional tests (lambdas or other functions) in
conditions. These tests operate over bound variables, so it is important for
positive facts that bind with these variables to be listed in the skill before
the tests that use them.
```python
@Skill(Fact(value=V('a')) &
       Fact(value=V('b')) &
       TEST(lambda a, b: a > b) &
       Fact(value=V('c')) &
       TEST(lambda b, c: b > c))
def three_values(a, b, c):
    print("{} is greater than {} is greater than {}".format(a, b, c))
```

It is also possible to bind *facts* to variables as well.
```python
@Skill(V('name_fact') << Fact(name=V('name')))
def found_name(name_fact):
    print("I found a name fact {}".format(name_fact)
```

Finally, skills also support nested matching using the double underscore. Imagine that the following facts are in the working memory:
```python
Fact(name="scissors", against={"scissors": 0, "rock": -1, "paper": 1})
Fact(name="paper", against={"scissors": -1, "rock": 1, "paper": 0})
Fact(name="rock", against={"scissors": 1, "rock": 0, "paper": -1})
```

Given, these facts, we might have a skill like the following:
```python
@Skill(Fact(name=V('name'), against__scissors=1, against__paper=-1))
def what_wins_to_scissors_and_losses_to_paper(name):
    print(name)
```

### Working Memory

To engage in reasoning *facts* and *skills* are loaded into a **WorkingMemory**, which facilitates the matching and application of skills to facts.

Here is how you create a working memory:

```python
wm = WorkingMemory()
```

Once a memory has been created, then facts can be added to it.
```python
f1 = Fact(light_color="red")
wm.add_fact(f1)
```

Note, facts added to the working memory cannot contain any variables or they will trigger an exception. Additionally, once a fact has been added to working memory it is assigned a unique internal identifier.

This makes it possible to update the fact.
```python
f1['light_color'] = "green"
wm.update_fact(f1)
```

It also make it possible to remove the fact.
```python
wm.remove_fact(f1)
```

When updating a fact, note that it is not updated in the working memory until
the `update_fact` method is called on it. An update essentially equates to
removing and re-adding the fact.

Skills can also be added to the working memory. When they are added, then the
the `wm` variable is added to the scope of the function. This `wm` variable
points to the working memory the skill has been added to, and can be used to
update the working memory.
```python
>>> f1 = Fact(light_color="red")
>>> 
>>> @Skill(V('fact') << Fact(light_color="red"))
>>> def make_green(fact):
>>>	print('making green')
>>>     fact['light_color'] = 'green'
>>>     wm.update_fact(fact)
>>> 
>>> @Skill(V('fact') << Fact(light_color="green"))
>>> def make_red(fact):
>>>	print('making red')
>>>     fact['light_color'] = 'red'
>>>     wm.update_fact(fact)
>>> 
>>> light_wm = WorkingMemory()
>>> light_wm.add_fact(f1)
>>> light_wm.add_skill(make_green)
>>> light_wm.add_skill(make_red)
```

Once the above fact and skills have been added the working memory can be run.
```python
>>> light_wm.run(5)
making green
making red
making green
making red
making green
```

The number passed to run denotes how many rules the working memory should fire
before terminating.

In addition to this high-level function for running the working memory, there
are also some lower-level capabilities that can be used to more closely control
the rule execution.

For example, you can get all the skill matches.
```python
matches = [match for match in light_wm.get_skill_matches()]
```

You can fire one of the matches.
```python
matches[0].fire()
```


[experta]: https://github.com/nilp0inter/experta
[doorenbos]: http://reports-archive.adm.cs.cmu.edu/anon/1995/CMU-CS-95-113.pdf
[image]: https://travis-ci.com/cmaclell/py_rete.svg?branch=master
[travis]: https://travis-ci.com/cmaclell/py_rete
[coveralls-badge]: https://coveralls.io/repos/github/cmaclell/py_rete/badge.svg?branch=master
[coveralls-repo]: https://coveralls.io/github/cmaclell/py_rete?branch=master
