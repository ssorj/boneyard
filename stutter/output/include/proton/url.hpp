namespace proton {

class url {
  public:
    url() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}