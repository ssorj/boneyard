namespace proton {

class reactor {
  public:
    reactor() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}