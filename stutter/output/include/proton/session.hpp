namespace proton {

class session {
  public:
    session() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}