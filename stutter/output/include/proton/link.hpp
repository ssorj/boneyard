namespace proton {

class link {
  public:
    link() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}