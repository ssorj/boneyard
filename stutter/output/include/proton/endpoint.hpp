namespace proton {

class endpoint {
  public:
    endpoint() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}