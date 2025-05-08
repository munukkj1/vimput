#include <iostream>
template<typename T>
T max(T a)
{
}

template<typename T, typename... Args>
T max(T v, Args ...args)
{
	T tail = max(args...);
	return v > tail ? v : tail;
}
