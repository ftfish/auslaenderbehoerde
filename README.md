# Time finder for Karlsruhe's Foreigners Authority

## Motivation
It is always a pain to find the next free time slot on the web page of Karlsruhe's Foreigners Authority. You have to click **every day** on the calendar only to find that the next possible appointment is in two months. However, appointments can be canceled and free slots can therefore pop up in the middle that is far nearer than in two months.

This small program helps automate that painful and inefficient process.

## Prerequisites
- Python 3+ (3.6 recommended)
- PyQt 5.6+ (5.10 recommended)
- BeautifulSoup 4


## Usage
Simply run `python find_appointments.py` in the console.

## Sample output
```
Using binary search to find first sure date...
	inspecting date 2018-03-22 , result = full
	inspecting date 2018-04-16 , result = available!!
	inspecting date 2018-04-04 , result = full
	inspecting date 2018-04-10 , result = available!!
	inspecting date 2018-04-06 , result = full
	inspecting date 2018-04-09 , result = available!!
First sure date: 2018-04-09 ['11:30', '12:00', '13:30', '14:00', '14:30', '15:00']
Trying to find earlier free slots...
	inspecting date 2018-02-08 , result = full
	inspecting date 2018-02-09 , result = full
	inspecting date 2018-02-12 , result = full
	...
	inspecting date 2018-04-06 , result = full
Found 0 earlier dates.
```
You **might** be lucky and might find earlier dates.
