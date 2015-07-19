
CXXFLAGS := -Werror -g -fno-omit-frame-pointer -pthread

CPPSOURCES = $(wildcard *.cpp) 
CCSOURCES = $(wildcard *.cc) 
OBJECTS = $(CPPSOURCES:.cpp=.o) $(CCSOURCES:.cc=.o)
TARGETS = $(basename $(CCSOURCES))

all: $(TARGETS)

$(TARGETS): $(OBJECTS)
	$(CXX) $(CXXFLAGS) -o $@ $(OBJECTS)

clean:
	rm -rf $(TARGET) $(OBJECTS)

