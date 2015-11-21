namespace proton {

class handler {
  public:
    handler() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}