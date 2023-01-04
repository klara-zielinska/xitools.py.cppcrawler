class TrivialA
{
public:
	int foo(int);
	char bar(char, int);
};

// comment

int TrivialA::foo(  int  x  ) { return x + 1; }
int TrivialA::bar(  char  c,	int n  ) { return c + n; }
