============
Bill Tracker
============

Utility to automatically parse bank account and credit card statements for more streamlined bill tracking.

Currently supports:

- PNC Bank (pdf)
- Chase (pdf)
- FNB (pdf)
- Discover (csv)

Installation
============

``git clone https://github.com/mabelechols/bill_tracker.git .``

``pip install ./bill_tracker``

``python -m bill -h``

How to run
==========
``python -m bill [-h] statement_dir [output_dir] [category_file]``

Positional Arguments:
 
 statement_dir    Directory containing bank statements

 output_dir       Directory to output .csv into

 category_file    Directory of categories.csv to use for categorization

Categories
============

categories.csv consists of categorizations in the following form:
``([reg_ex], [category_1], [category_2], ...)``

``[reg_ex]`` is used to search transactions. If a match is found, the item is considered categorized. The first match is always used.

``[category_1]`` is required, and is the main category of the item. Special arguments `ignore` and `~` can be used for the following:

- ``ignore`` : Do not record items matching this search into the output
- ``~`` : No category

Categories may have more or less arbitrary names, excluding the use of the following characters: ``.,/\``

``[category_2]`` and so forth are optional, and allow for the use of subcategories. An alternative way to identify subcategories would be to seperate categories with a `.`. For example:

``[reg_ex] ,food, grocery, bread`` is equivalent to ``[reg_ex], food.grocery.bread``

A mix may also be used if desired, for example:

``[reg_ex] ,food.grocery, bread`` and ``[reg_ex], food, grocery.bread`` are both equivalent to the above statements
