namespace proton {

class acceptor {
  public:
    acceptor() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}