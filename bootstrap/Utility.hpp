#ifndef SYSMEL_UTILITY_HPP
#define SYSMEL_UTILITY_HPP

#include <string>

std::string path_dirname(const std::string &path);
std::string path_basename(const std::string &path);
std::string path_join(const std::string &leftPath, const std::string &rightPath);

#endif //SYSMEL_UTILITY_HPP