#include <iostream>
template<typename T, typename... Args>
T max(T v, Args ...args)
{
	T tail = max(args...);
	return v > tail ? v : tail;
}
