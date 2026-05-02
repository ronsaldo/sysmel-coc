#include "Utility.hpp"

std::string
path_dirname(const std::string &path)
{
    size_t lastSeparatorIndex = 0;
    for(size_t i = 0; i < path.size(); ++i)
    {
        auto c = path[i];
        if(c == '/' || c == '\\')
            lastSeparatorIndex = i;
    }

    return path.substr(0, lastSeparatorIndex);
}

std::string
path_basename(const std::string &path)
{
    size_t lastSeparatorIndex = 0;
    bool hasSeparator = false;
    for(size_t i = 0; i < path.size(); ++i)
    {
        auto c = path[i];
        if(c == '/' || c == '\\')
        {
            lastSeparatorIndex = i;
            hasSeparator = true;
        }
    }

    if(!hasSeparator)
        return path;

    return path.substr(lastSeparatorIndex + 1);
}

std::string
path_join(const std::string &leftPath, const std::string &rightPath)
{
    std::string result = leftPath;
    if(!result.empty())
    {
        auto lastC = result.back();
        if(lastC != '\\' && lastC != '/')
            result.push_back('/');
    }

    result += rightPath;
    return result;
}