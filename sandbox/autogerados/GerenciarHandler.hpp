#ifndef GERENCIARHANDLER_HPP
#define GERENCIARHANDLER_HPP

#include <string>
#include <vector>
#include <memory>

class GerenciarHandler {
public:
    GerenciarHandler() = default;
    ~GerenciarHandler() = default;
    
    // Metodos
    void execute();
    
private:
    int status_;
};

#endif // GERENCIARHANDLER_HPP
