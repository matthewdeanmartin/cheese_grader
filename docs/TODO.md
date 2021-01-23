TODO
---
END GOAL – Library that can take list of current deps & transitive deps & say:

Score is inverse to how frequent it is.
--- 
- is it a parked package (uncommon)
- is it a test/experiment/junk package (5%?)
- is it even valid 2.7 or 3.x? (5%?) Compliable, formatible. 
- is it name conflicted with stdlib? uncommon
- is it stale? – VERY COMMON
	- few releases, old releases
- is it abandoned? – VERY COMMON
	- archived github
	- dead home page
- is it ignored?—VERY COMMON
	- few downloads
- does it have native bits (may be non issue or important issue)

TODO
--
- download all meta data
	- put into db for easy query.
	- keep json for reprocessing.
- list graph of all deps
- function to evaluate each sort of quality
- inverse frequency metric weighting. (yeah, it is rarely downloaded, but so are all packages), maybe incorporate “ideal” params, (e.g. if it is important for a package to demonstrate reliability via popularity, or not because we know it is a rare use case)
- 


