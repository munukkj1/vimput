#include <iostream>
template<typename T>
T max(T a)
{
	return a;
}

template<typename T, typename... Args>
T max(T v, Args ...args)
{
	T tail = max(args...);
	return v > tail ? v : tail;
}


int main()
{
	std::cout << "max(1,2) = " << max(1,2) << std::endl;
	std::cout << "max(3.4,5.6) = " << max(3.4,5.6) << std::endl;
	std::cout << "max(-6, 4) = " << max(-6, 4) << std::endl;
	std::cout << "max(1,-2,-5, 56, 8, 100, -100, 20) = " << max(1,-2,-5, 56, 8, 100, -100, 20) << std::endl;
	return 0;
}
