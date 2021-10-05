CFLAGS = -std=gnu99 -w
LIBS = -lpthread -pthread
SOURCES1 = src/app.c
OUT1 = app

default:
	gcc -Iinc $(CFLAGS) $(LIBS) -o $(OUT1) $(SOURCES1)
debug:
	gcc -Iinc -g $(CFLAGS) $(LIBS) -o $(OUT1) $(SOURCES1)
all:
	gcc -Iinc $(CFLAGS) $(LIBS) -o $(OUT1) $(SOURCES1)
clean:
	rm $(OUT1)
