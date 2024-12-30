# fledge-project
Project for Masters Thesis

Note that north plugin needs kafka-python.
Reqs file not yet done.

## Summary:
Prototype to read data from REST API, modify it, and send it with Kafka was designed 
and developed in this project. This project shows an example of how Fledge can be 
used in the process of gathering data. FledgePOWER was selected as the base for the 
prototype, but all the features that were used are also present in base version of Fledge.
The amount of custom code needed for the plugins was relatively small, but there 
were many issues and challenges during the development. During the process the 
complexity of the prototype was decreased, and focus was put on building a minimal 
viable prototype. Many features that FledgePOWER has, like pivot modelling, were 
not used because of their (relative) complexity. The plugins created are simple but 
demonstrate the functionality of the system. I hope that this thesis can also serve as a 
guide for newcomers looking to build new plugins to Fledge. Detailed information of 
how the system was set up for the testing can be used to replicate this prototype.
In evaluation the system was tested with Raspberry Pi Model B+, which has one of 
the lowest computational capabilities able to run Fledge. Even with it the system was 
usable for it’s purpose. With more powerful hardware the bandwidth of connection 
became the bottleneck, but searching for a definitive limit was not one of the goals for 
testing.

## Link to Thesis:
https://urn.fi/URN:NBN:fi:oulu-202412177354

## Installation using Docker:

`cd fledge-docker`

`docker compose up -d`

